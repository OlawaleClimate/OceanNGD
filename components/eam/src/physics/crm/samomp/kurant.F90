
module kurant_mod
   use params, only: asyncid
   use task_util_mod
   implicit none

   contains

   subroutine kurant(ncrms)
      use vars
      use sgs, only: kurant_sgs
      use params, only: crm_rknd
      implicit none
      integer, intent(in) :: ncrms
      integer i, j, k, ncycle1(1),ncycle2(1),icrm
      real(crm_rknd), allocatable :: wm (:,:)  ! maximum vertical wind velocity
      real(crm_rknd), allocatable :: uhm(:,:) ! maximum horizontal wind velocity
      real(crm_rknd) cfl, cfl_sgs, tmp
      integer, parameter :: max_ncycle = 4

      allocate(wm (ncrms,nz))
      allocate(uhm(ncrms,nz))
      !$omp target enter data map(alloc: wm  )
      !$omp target enter data map(alloc: uhm )

      ncycle = 1
      !$omp target teams distribute parallel do collapse(2)
      do k = 1 , nz
        do icrm = 1 , ncrms
          wm(icrm,k) = 0.
          uhm(icrm,k) = 0.
        enddo
      enddo

      !$omp target teams distribute parallel do collapse(4)
      do k = 1,nzm
        do j = 1 , ny
          do i = 1 , nx
            do icrm = 1 , ncrms
              tmp = abs(w(icrm,i,j,k))
              !$omp atomic update
              wm(icrm,k) = max( wm(icrm,k) , tmp )

              tmp = sqrt(u(icrm,i,j,k)**2+YES3D*v(icrm,i,j,k)**2)
              !$omp atomic update
              uhm(icrm,k) = max( uhm(icrm,k) , tmp )
            enddo
          enddo
        enddo
      enddo

      cfl = 0.
      !$omp target teams distribute parallel do reduction(max:cfl) collapse(2)
      do k=1,nzm
        do icrm = 1 , ncrms
          tmp = max( uhm(icrm,k)*dt*sqrt((1.D0/dx)**2+YES3D*(1.D0/dy)**2) , max(wm(icrm,k),wm(icrm,k+1))*dt/(dz(icrm)*adzw(icrm,k)) )
          cfl = max( cfl , tmp )
        end do
      end do

      call kurant_sgs(ncrms,cfl)
      !$omp taskwait
      ncycle = max(ncycle,max(1,ceiling(cfl/0.7D0)))

#ifdef MMF_FIXED_SUBCYCLE
      ncycle = max_ncycle
#endif

      if(ncycle.gt.max_ncycle) then
        !$omp target update from(wm)
        !$omp target update from(uhm)
        !$omp target update from(tabs)
        if(masterproc) print *,'kurant() - the number of cycles exceeded max_ncycle = ',max_ncycle
        do icrm = 1 , ncrms
          write(0, 5550) cfl, cfl_sgs, latitude(icrm,1,1), longitude(icrm,1,1)
          do k=1, nzm
            write(0, 5551) k, wm(icrm,k), uhm(icrm,k), tabs(icrm,1,1,k)
          end do
        end do
        call task_abort()
      end if

      !$omp target exit data map(delete: wm)
      !$omp target exit data map(delete: uhm)
      deallocate(wm )
      deallocate(uhm)

5550 format('kurant() - cfl: ',f12.2,'  cfl_sgs: ',f12.2,'  lat: ',f6.2,'  lon: ',f6.2)
5551 format('k: ',i5,'  wm: ',f10.2,'  uhm: ',f10.2,'  tabs: ',f8.2)

   end subroutine kurant

end module kurant_mod
